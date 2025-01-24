import styles from '../viewport.module.css';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  // Function to generate page numbers to display
  const getPageNumbers = () => {
    const pages: number[] = [];
    const maxVisiblePages = 7; // Show at most 7 page numbers
    const halfVisible = Math.floor(maxVisiblePages / 2);

    // Always show first and last page
    if (totalPages <= maxVisiblePages) {
      // If total pages is less than max visible, show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Add first page
      pages.push(1);

      // Calculate range around current page
      let rangeStart = Math.max(2, currentPage - halfVisible);
      let rangeEnd = Math.min(totalPages - 1, currentPage + halfVisible);

      // Adjust range if at edges
      if (currentPage <= halfVisible + 1) {
        rangeEnd = maxVisiblePages - 1;
      } else if (currentPage >= totalPages - halfVisible) {
        rangeStart = totalPages - maxVisiblePages + 2;
      }

      // Add ellipsis if needed
      if (rangeStart > 2) {
        pages.push(-1); // -1 represents ellipsis
      }

      // Add range pages
      for (let i = rangeStart; i <= rangeEnd; i++) {
        pages.push(i);
      }

      // Add ellipsis if needed
      if (rangeEnd < totalPages - 1) {
        pages.push(-2); // -2 represents ellipsis
      }

      // Add last page
      pages.push(totalPages);
    }

    return pages;
  };
  
  return (
    <div className={styles.paginationContainer}>
      <div className={styles.paginationWrapper}>
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          className={styles.paginationButton}
          disabled={currentPage === 1}
        >
          ←
        </button>

        {getPageNumbers().map((pageNum, index) => {
          if (pageNum < 0) {
            // Render ellipsis
            return <span key={`ellipsis-${index}`} className={styles.paginationEllipsis}>...</span>;
          }
          
          return (
            <button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              className={currentPage === pageNum ? styles.paginationButtonActive : styles.paginationButton}
            >
              {pageNum}
            </button>
          );
        })}

        <button
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          className={styles.paginationButton}
          disabled={currentPage === totalPages}
        >
          →
        </button>
      </div>
    </div>
  );
} 