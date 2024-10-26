// Accessibility manager configuration
const AccessibilityConfig = {
    // Prevent invalid range errors
    handleSelectionChange: function(e) {
        try {
            const selection = window.getSelection();
            if (selection && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                if (range && range.startContainer && range.endContainer) {
                    // Valid range, proceed with accessibility handling
                    return true;
                }
            }
        } catch (err) {
            console.warn('Selection change error:', err);
        }
        return false;
    },

    // Initialize accessibility features
    init: function() {
        document.addEventListener('selectionchange', this.handleSelectionChange);
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', function() {
    AccessibilityConfig.init();
});
