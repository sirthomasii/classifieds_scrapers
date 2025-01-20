import styles from '../viewport.module.css';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;
  
  return (
    <div className={styles.paginationContainer}>
      <div className={styles.paginationWrapper}>
        {[...Array(totalPages)].map((_, i) => {
          // Show current page, 2 before and 2 after
          const shouldShow = 
            i === 0 || // First page
            i === totalPages - 1 || // Last page
            (i >= currentPage - 2 && i <= currentPage + 2); // Current range
          
          if (!shouldShow) {
            if (i === currentPage - 3 || i === currentPage + 3) {
              return <span key={i} style={{ color: 'white' }}>...</span>;
            }
            return null;
          }
          
          return (
            <button
              key={i}
              onClick={() => onPageChange(i + 1)}
              className={currentPage === i + 1 ? styles.paginationButtonActive : styles.paginationButton}
            >
              {i + 1}
            </button>
          );
        })}
      </div>
    </div>
  );
} 