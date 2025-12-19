/**
 * Skeleton Loaders pour les états de chargement
 */
export const MessageSkeleton = () => {
  return (
    <div className="flex gap-3 p-4 animate-pulse">
      <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-700 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
        <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-5/6" />
      </div>
    </div>
  )
}

export const ChatSkeleton = () => {
  return (
    <div className="space-y-4 p-4">
      <MessageSkeleton />
      <MessageSkeleton />
      <MessageSkeleton />
    </div>
  )
}

export const SessionSkeleton = () => {
  return (
    <div className="p-3 border-b border-gray-200 dark:border-gray-700 animate-pulse">
      <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4 mb-2" />
      <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
    </div>
  )
}

export const SidebarSkeleton = () => {
  return (
    <div className="space-y-2">
      <SessionSkeleton />
      <SessionSkeleton />
      <SessionSkeleton />
      <SessionSkeleton />
    </div>
  )
}

export const DocumentSkeleton = () => {
  return (
    <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gray-300 dark:bg-gray-700 rounded" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-2/3" />
          <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/3" />
        </div>
      </div>
    </div>
  )
}

export const ButtonSkeleton = ({ className = "" }) => {
  return (
    <div className={`h-10 bg-gray-300 dark:bg-gray-700 rounded animate-pulse ${className}`} />
  )
}

export const InputSkeleton = () => {
  return (
    <div className="h-12 bg-gray-300 dark:bg-gray-700 rounded-lg animate-pulse" />
  )
}

