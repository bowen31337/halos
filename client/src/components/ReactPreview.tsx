import { useEffect, useRef, useState, useMemo } from 'react'
import { createRoot, Root } from 'react-dom/client'

interface ReactPreviewProps {
  code: string
  onError?: (error: Error) => void
  onReady?: () => void
}

interface ModuleType {
  default?: React.ComponentType<any>
  [key: string]: any
}

/**
 * ReactPreview Component
 *
 * Renders React components in an isolated iframe with hot reload support.
 *
 * Features:
 * - Live preview of React components
 * - Hot reload on code changes
 * - Error boundary for graceful error handling
 * - Isolated execution environment
 * - Support for default exports and named exports
 */
export function ReactPreview({ code, onError, onReady }: ReactPreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const cleanupRef = useRef<(() => void) | null>(null)

  // Prepare the code for execution in the iframe
  const iframeContent = useMemo(() => {
    const codeStr = JSON.stringify(code)
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>React Component Preview</title>
          <style>
            * {
              margin: 0;
              padding: 0;
              box-sizing: border-box;
            }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
              padding: 20px;
              background: #ffffff;
              color: #1a1a1a;
            }
            #root {
              min-height: 100vh;
            }
            .error-boundary {
              padding: 20px;
              background: #fee;
              border: 1px solid #fcc;
              border-radius: 8px;
              color: #c33;
            }
            .error-boundary h3 {
              margin-bottom: 10px;
            }
            .error-boundary pre {
              background: #f5f5f5;
              padding: 10px;
              border-radius: 4px;
              overflow-x: auto;
              font-size: 12px;
            }
          </style>
        </head>
        <body>
          <div id="root"></div>
          <script>
            // Error boundary class
            class ErrorBoundary extends React.Component {
              constructor(props) {
                super(props);
                this.state = { hasError: false, error: null };
              }

              static getDerivedStateFromError(error) {
                return { hasError: true, error };
              }

              componentDidCatch(error, errorInfo) {
                console.error('Component error:', error, errorInfo);
              }

              render() {
                if (this.state.hasError) {
                  return React.createElement('div', { className: 'error-boundary' },
                    React.createElement('h3', null, '⚠️ Component Error'),
                    React.createElement('p', null, this.state.error?.toString() || 'Unknown error'),
                    this.state.error?.stack && React.createElement('pre', null, this.state.error.stack)
                  );
                }
                return this.props.children;
              }
            }

            // Transform and execute code
            async function renderComponent() {
              try {
                // Clear previous content
                const root = document.getElementById('root');
                root.innerHTML = '';

                // Transform JSX using Babel standalone
                const transformedCode = Babel.transform(${codeStr}, {
                  presets: [['react', { runtime: 'automatic' }]],
                  filename: 'component.jsx'
                }).code;

                // Create a function from the transformed code
                const moduleFactory = new Function('React', 'require', transformedCode + '\\nreturn module;');

                // Create a mock require function
                const mockRequire = (name) => {
                  if (name === 'react') return React;
                  throw new Error('Module "' + name + '" is not available in preview');
                };

                // Execute the code to get the module
                const module = moduleFactory(React, mockRequire);

                // Get the component (try default export, then named exports)
                let Component = module.default;
                if (!Component && typeof module === 'function') {
                  Component = module;
                }
                if (!Component) {
                  // Try to find the first React component in exports
                  for (const key in module) {
                    if (typeof module[key] === 'function' && module[key].$$typeof) {
                      Component = module[key];
                      break;
                    }
                  }
                }

                if (!Component) {
                  throw new Error('No React component found in code. Make sure to export a component.');
                }

                // Render with error boundary
                const rootElement = React.createElement(ErrorBoundary, null,
                  React.createElement(Component, {
                    onRefresh: renderComponent
                  })
                );

                const ReactDOMRoot = ReactDOM.createRoot(root);
                ReactDOMRoot.render(rootElement);

                // Notify parent that preview is ready
                window.parent.postMessage({ type: 'preview-ready' }, '*');
              } catch (err) {
                console.error('Preview error:', err);
                const root = document.getElementById('root');
                root.innerHTML = '<div class="error-boundary"><h3>⚠️ Preview Error</h3><p>' + (err.message || err) + '</p>' + (err.stack ? '<pre>' + err.stack + '</pre>' : '') + '</div>';
                window.parent.postMessage({ type: 'preview-error', error: err.message }, '*');
              }
            }

            // Load React and Babel from CDN
            const loadScript = (src) => {
              return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = () => reject(new Error('Failed to load ' + src));
                document.head.appendChild(script);
              });
            };

            Promise.all([
              loadScript('https://unpkg.com/react@18/umd/react.production.min.js'),
              loadScript('https://unpkg.com/react-dom@18/umd/react-dom.production.min.js'),
              loadScript('https://unpkg.com/@babel/standalone/babel.min.js')
            ]).then(() => {
              renderComponent();
            }).catch((err) => {
              console.error('Failed to load dependencies:', err);
              document.getElementById('root').innerHTML = '<div class="error-boundary"><h3>⚠️ Failed to load dependencies</h3><p>' + (err.message || err) + '</p></div>';
            });
          </script>
        </body>
      </html>
    `
  }, [code])

  // Handle messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'preview-ready') {
        setIsLoading(false)
        setError(null)
        onReady?.()
      } else if (event.data.type === 'preview-error') {
        setIsLoading(false)
        setError(event.data.error)
        onError?.(new Error(event.data.error))
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [onError, onReady])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current()
      }
    }
  }, [])

  // Reload iframe when code changes (hot reload)
  useEffect(() => {
    const iframe = iframeRef.current
    if (iframe && iframe.contentWindow) {
      setIsLoading(true)
      setError(null)
      // Force reload by resetting src
      iframe.srcdoc = iframeContent
    }
  }, [iframeContent])

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            React Preview
          </span>
          {isLoading && (
            <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500"></div>
              Loading...
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Hot reload enabled
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 relative">
        <iframe
          ref={iframeRef}
          srcDoc={iframeContent}
          className="w-full h-full border-0"
          title="React Component Preview"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 border-t border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
          <div className="flex items-start gap-2">
            <span className="text-red-500">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-700 dark:text-red-400">
                Component Error
              </p>
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400 flex justify-between">
        <span>React 18 + Babel</span>
        <span>Isolated environment</span>
      </div>
    </div>
  )
}
