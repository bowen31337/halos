/**
 * Branch Indicator Component
 * Shows when the current conversation is a branch
 */

import { defineComponent, computed } from 'vue'
import { useBranchingStore } from '@/stores/branchingStore'
import { storeToRefs } from 'pinia'

export default defineComponent({
  name: 'BranchIndicator',
  props: {
    conversationId: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const branchingStore = useBranchingStore()
    const { branchPath, currentBranchInfo } = storeToRefs(branchingStore)

    const isBranch = computed(() => {
      return currentBranchInfo.value?.isBranch || branchPath.value.length > 1
    })

    const branchName = computed(() => {
      if (!isBranch.value) return null
      const currentBranch = branchPath.value[branchPath.value.length - 1]
      return currentBranch?.branch_name || 'Branch'
    })

    const branchColor = computed(() => {
      const currentBranch = branchPath.value[branchPath.value.length - 1]
      return currentBranch?.branch_color || '#ff6b6b'
    })

    const rootConversationId = computed(() => {
      return branchPath.value[0]?.id || null
    })

    return {
      isBranch,
      branchName,
      branchColor,
      rootConversationId
    }
  }
})