"use client";

interface MobileHeaderProps {
  onToggleSidebar: () => void;
}

export function MobileHeader({ onToggleSidebar }: MobileHeaderProps) {
  return (
    <header className="md:hidden flex items-center h-12 px-3 border-b border-gray-200 bg-white">
      <button
        onClick={onToggleSidebar}
        className="p-1.5 rounded-md text-gray-600 hover:bg-gray-100"
        aria-label="Menu"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <span className="ml-2 text-sm font-semibold text-brand-700">
        Legal AI
      </span>
    </header>
  );
}
