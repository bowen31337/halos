/**
 * Branch Tree Component
 * Visualizes conversation branches in a tree structure
 */

import { defineComponent, computed, ref, watch } from 'vue'
import { useBranchingStore } from '@/stores/branchingStore'
import { useConversationStore } from '@/stores/conversationStore'
import { storeToRefs } from 'pinia'

export default defineComponent({
  name: 'BranchTree',
  props: {
    conversationId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const branchingStore = useBranchingStore()
    const conversationStore = useConversationStore()
    const { branches, branchPath, isBranching, error } = storeToRefs(branchingStore)

    const isExpanded = ref(true)
    const selectedBranchId = ref<string | null>(null)

    // Load branch data when conversation changes
    watch(
      () => props.conversationId,
      async (newId) => {
        if (newId) {
          await branchingStore.initialize(newId)
          selectedBranchId.value = newId
        }
      },
      { immediate: true }
    )

    const currentConversation = computed(() => {
      return conversationStore.conversations.find(c => c.id === props.conversationId)
    })

    const hasBranches = computed(() => branches.value.length > 0)

    const isCurrentBranch = computed(() => {
      return branchPath.value.length <= 1
    })

    const switchToBranch = async (branchId: string) => {
      if (branchId === props.conversationId || isBranching.value) return

      try {
        await branchingStore.switchBranch(props.conversationId, branchId)
        conversationStore.setCurrentConversation(branchId)
        selectedBranchId.value = branchId
      } catch (err) {
        console.error('Failed to switch branch:', err)
      }
    }

    const createNewBranch = async () => {
      if (isBranching.value || !currentConversation.value) return

      try {
        // Use the last assistant message as branch point
        const messages = conversationStore.messages
        const lastAssistantMessage = messages
          .filter(m => m.role === 'assistant')
          .slice(-1)[0]

        if (lastAssistantMessage) {
          const newBranch = await branchingStore.createBranch(
            props.conversationId,
            lastAssistantMessage.id,
            `New Branch - ${new Date().toLocaleString()}`
          )

          // Switch to new branch
          conversationStore.setCurrentConversation(newBranch.id)
          selectedBranchId.value = newBranch.id
        }
      } catch (err) {
        console.error('Failed to create branch:', err)
      }
    }

    const formatBranchName = (branch: any) => {
      if (branch.branch_name) {
        return branch.branch_name
      }
      return `Branch ${branches.value.indexOf(branch) + 1}`
    }

    const getBranchColor = (branch: any) => {
      return branch.branch_color || '#ff6b6b'
    }

    return {
      branches,
      branchPath,
      isExpanded,
      selectedBranchId,
      isBranching,
      error,
      currentConversation,
      hasBranches,
      isCurrentBranch,
      switchToBranch,
      createNewBranch,
      formatBranchName,
      getBranchColor
    }
  }
})