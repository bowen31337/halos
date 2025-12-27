/**
 * File type detection and language mapping utilities.
 */

export interface FileType {
  type: 'image' | 'code' | 'text' | 'binary'
  category: string
  language?: string
  mime?: string
  icon?: string
}

/**
 * File extension to language mapping for syntax highlighting.
 */
const LANGUAGE_MAP: Record<string, string> = {
  // Python
  '.py': 'python',
  '.pyw': 'python',
  '.pyi': 'python',

  // JavaScript
  '.js': 'javascript',
  '.jsx': 'javascript',
  '.mjs': 'javascript',
  '.cjs': 'javascript',

  // TypeScript
  '.ts': 'typescript',
  '.tsx': 'typescript',

  // Web
  '.html': 'html',
  '.htm': 'html',
  '.css': 'css',
  '.scss': 'scss',
  '.sass': 'sass',
  '.less': 'less',
  '.json': 'json',
  '.xml': 'xml',

  // Rust
  '.rs': 'rust',

  // Go
  '.go': 'go',

  // C/C++
  '.c': 'c',
  '.cpp': 'cpp',
  '.cc': 'cpp',
  '.cxx': 'cpp',
  '.h': 'c',
  '.hpp': 'cpp',

  // Java
  '.java': 'java',
  '.kt': 'kotlin',
  '.scala': 'scala',

  // C#
  '.cs': 'csharp',
  '.fs': 'fsharp',

  // Shell
  '.sh': 'shell',
  '.bash': 'shell',
  '.zsh': 'shell',
  '.fish': 'shell',

  // PowerShell
  '.ps1': 'powershell',
  '.psm1': 'powershell',

  // SQL
  '.sql': 'sql',
  '.pgsql': 'sql',
  '.plsql': 'sql',

  // Markdown
  '.md': 'markdown',
  '.markdown': 'markdown',

  // YAML
  '.yml': 'yaml',
  '.yaml': 'yaml',

  // TOML
  '.toml': 'toml',

  // Config files
  '.ini': 'ini',
  '.conf': 'ini',
  '.config': 'ini',

  // Docker
  'dockerfile': 'dockerfile',
  '.dockerfile': 'dockerfile',

  // Other text files
  '.txt': 'text',
  '.csv': 'csv',
  '.tsv': 'tsv',
  '.log': 'text',

  // Ruby
  '.rb': 'ruby',
  '.gemfile': 'ruby',

  // PHP
  '.php': 'php',

  // Swift
  '.swift': 'swift',

  // Dart
  '.dart': 'dart',

  // R
  '.r': 'r',
  '.rmd': 'rmarkdown',

  // MATLAB
  '.m': 'matlab',

  // Lua
  '.lua': 'lua',

  // Perl
  '.pl': 'perl',
  '.pm': 'perl',

  // Haskell
  '.hs': 'haskell',

  // Elixir
  '.ex': 'elixir',
  '.exs': 'elixir',

  // Clojure
  '.clj': 'clojure',
  '.cljs': 'clojure',

  // Groovy
  '.groovy': 'groovy',
  '.gvy': 'groovy',

  // Vue
  '.vue': 'vue',

  // Svelte
  '.svelte': 'svelte',

  // Assembly
  '.asm': 'assembly',
  '.s': 'assembly',

  // Makefile
  'makefile': 'makefile',
  '.mak': 'makefile',

  // Protocol Buffers
  '.proto': 'proto',

  // GraphQL
  '.graphql': 'graphql',
  '.gql': 'graphql',

  // Terraform
  '.tf': 'terraform',
  '.hcl': 'terraform',

  // Ansible
  '.yml': 'yaml', // Ansible playbooks are YAML
}

/**
 * Image file extensions.
 */
const IMAGE_EXTENSIONS = [
  '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tif', '.tiff'
]

/**
 * Binary file extensions (display as binary, not editable).
 */
const BINARY_EXTENSIONS = [
  '.exe', '.dll', '.so', '.dylib', '.bin', '.o', '.obj', '.a', '.lib',
  '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz', '.zipx',
  '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
  '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac', '.ogg',
  '.ttf', '.otf', '.woff', '.woff2', '.eot',
]

/**
 * Detect file type from filename or File object.
 */
export function detectFileType(file: string | File): FileType {
  const filename = typeof file === 'string' ? file : file.name
  const ext = getFileExtension(filename).toLowerCase()

  // Check for image
  if (IMAGE_EXTENSIONS.includes(ext)) {
    return {
      type: 'image',
      category: 'image',
      mime: getMimeType(ext),
      icon: '🖼️'
    }
  }

  // Check for binary
  if (BINARY_EXTENSIONS.includes(ext)) {
    return {
      type: 'binary',
      category: 'binary',
      icon: '📦'
    }
  }

  // Check for code/text files
  const language = LANGUAGE_MAP[ext] || LANGUAGE_MAP[filename.toLowerCase()]

  if (language) {
    return {
      type: 'code',
      category: 'code',
      language,
      mime: getMimeType(ext),
      icon: getLanguageIcon(language)
    }
  }

  // Default to text
  return {
    type: 'text',
    category: 'text',
    language: 'text',
    icon: '📄'
  }
}

/**
 * Get file extension from filename.
 */
export function getFileExtension(filename: string): string {
  const lastDot = filename.lastIndexOf('.')
  const lastSlash = Math.max(
    filename.lastIndexOf('/'),
    filename.lastIndexOf('\\')
  )

  // Handle cases like "dockerfile" or "makefile" (no extension)
  if (lastDot === -1 || lastDot < lastSlash) {
    return filename.toLowerCase()
  }

  return filename.slice(lastDot)
}

/**
 * Get MIME type from extension.
 */
function getMimeType(ext: string): string {
  const mimeMap: Record<string, string> = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
  }

  return mimeMap[ext.toLowerCase()] || 'application/octet-stream'
}

/**
 * Get icon emoji for programming language.
 */
function getLanguageIcon(language: string): string {
  const iconMap: Record<string, string> = {
    'python': '🐍',
    'javascript': '⚡',
    'typescript': '📘',
    'java': '☕',
    'rust': '🦀',
    'go': '🐹',
    'c': '©️',
    'cpp': '©️',
    'csharp': '💜',
    'ruby': '💎',
    'php': '🐘',
    'swift': '🍎',
    'kotlin': '🤖',
    'html': '🌐',
    'css': '🎨',
    'scss': '🎨',
    'shell': '💻',
    'powershell': '💠',
    'sql': '🗃️',
    'markdown': '📝',
    'yaml': '⚙️',
    'json': '📋',
    'dockerfile': '🐳',
    'text': '📄',
    'csv': '📊',
  }

  return iconMap[language] || '📄'
}

/**
 * Check if file is supported for preview/editing.
 */
export function isFileSupported(file: string | File): boolean {
  const fileType = detectFileType(file)
  return fileType.type !== 'binary'
}

/**
 * Get human-readable file description.
 */
export function getFileDescription(file: string | File): string {
  const fileType = detectFileType(file)

  if (fileType.type === 'image') {
    return 'Image file'
  }

  if (fileType.type === 'binary') {
    return 'Binary file (preview not available)'
  }

  if (fileType.language) {
    const languageName = getLanguageDisplayName(fileType.language)
    return `${languageName} file`
  }

  return 'Text file'
}

/**
 * Get display name for programming language.
 */
function getLanguageDisplayName(language: string): string {
  const nameMap: Record<string, string> = {
    'python': 'Python',
    'javascript': 'JavaScript',
    'typescript': 'TypeScript',
    'java': 'Java',
    'rust': 'Rust',
    'go': 'Go',
    'c': 'C',
    'cpp': 'C++',
    'csharp': 'C#',
    'ruby': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kotlin': 'Kotlin',
    'html': 'HTML',
    'css': 'CSS',
    'scss': 'SCSS',
    'shell': 'Shell',
    'bash': 'Bash',
    'powershell': 'PowerShell',
    'sql': 'SQL',
    'markdown': 'Markdown',
    'yaml': 'YAML',
    'json': 'JSON',
    'dockerfile': 'Dockerfile',
    'text': 'Plain Text',
    'csv': 'CSV',
  }

  return nameMap[language] || language.charAt(0).toUpperCase() + language.slice(1)
}

/**
 * Read file content as text (for code/text files).
 */
export async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string || '')
    reader.onerror = (e) => reject(new Error('Failed to read file'))
    reader.readAsText(file)
  })
}

/**
 * Read file as data URL (for images).
 */
export async function readFileAsDataURL(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string || '')
    reader.onerror = (e) => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}
