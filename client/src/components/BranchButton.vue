/**
 * Branch Button Component
 * Shows a branch button on messages that allows creating conversation branches
 */

import { defineComponent, computed, ref } from 'vue'
import { useBranchingStore } from '@/stores/branchingStore'
import { useConversationStore } from '@/stores/conversationStore'
import { storeToRefs } from 'pinia'

export default defineComponent({
  name: 'BranchButton',
  props: {
    messageId: {
      type: String,
      required: true
    },
    conversationId: {
      type: String,
      required: true
    },
    messageIndex: {
      type: Number,
      required: true
    },
    isAssistantMessage: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const branchingStore = useBranchingStore()
    const conversationStore = useConversationStore()
    const { isBranching, error } = storeToRefs(branchingStore)

    const showBranchButton = computed(() => {
      // Only show branch button on assistant messages
      // And only if this is not the last message
      const messages = conversationStore.messages
      const currentIndex = props.messageIndex
      return props.isAssistantMessage && currentIndex < messages.length - 1
    })

    const showTooltip = ref(false)
    const isHovered = ref(false)
    const isClicked = ref(false)

    const handleMouseEnter = () => {
      if (showBranchButton.value) {
        isHovered.value = true
        showTooltip.value = true
      }
    }

    const handleMouseLeave = () => {
      isHovered.value = false
      // Delay hiding tooltip to allow clicking
      setTimeout(() => {
        if (!isClicked.value) {
          showTooltip.value = false
        }
      }, 200)
    }

    const handleMouseDown = () => {
      isClicked.value = true
    }

    const handleMouseUp = () => {
      isClicked.value = false
    }

    const handleBranch = async (e: Event) => {
      e.stopPropagation()
      e.preventDefault()

      if (isBranching.value) return

      try {
        const newConversation = await branchingStore.createBranch(
          props.conversationId,
          props.messageId
        )

        // Switch to the new branch
        conversationStore.setCurrentConversation(newConversation.id)

        // Clear error on success
        branchingStore.clearError()
      } catch (err) {
        console.error('Failed to create branch:', err)
        // Error is handled by the store
      }
    }

    return {
      showBranchButton,
      showTooltip,
      isHovered,
      isClicked,
      isBranching,
      error,
      handleMouseEnter,
      handleMouseLeave,
      handleMouseDown,
      handleMouseUp,
      handleBranch
    }
  }
})