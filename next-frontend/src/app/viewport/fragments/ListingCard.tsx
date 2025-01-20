import { Publication } from '@/types/publication';
import styles from '../viewport.module.css';
import { getFlagComponent } from '../utils/flags';

interface ListingCardProps {
  item: Publication;
  getDisplayTitle: (item: Publication) => string;
}

export function ListingCard({ item, getDisplayTitle }: ListingCardProps) {
  return (
    <div 
      className={styles.itemCard}
      onClick={() => item.link && window.open(item.link, '_blank')}
    >
      <div className={styles.imageContainer}>
        {item.main_image && (
          <img
            src={item.main_image}
            alt={getDisplayTitle(item) || 'Product image'}
            className={styles.imageLoading}
            onError={(e) => {
              const imgElement = e.target as HTMLImageElement;
              imgElement.style.display = 'none';
              const container = imgElement.parentElement;
              if (container) {
                container.style.backgroundColor = '#333';
              }
            }}
            onLoad={(e) => {
              const imgElement = e.target as HTMLImageElement;
              imgElement.style.display = 'block';
              imgElement.classList.remove(styles.imageLoading);
            }}
            style={{ 
              objectFit: 'cover',
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%'
            }}
          />
        )}
      </div>
      <div className={styles.itemContent}>
        <div style={{ 
          fontSize: '16px', 
          fontWeight: 'bold',
          marginBottom: '8px',
          color: 'white',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
          lineHeight: '1.2em',
          maxHeight: '2.4em'  // 1.2em * 2 lines
        }}>
          {item.title?.english || item.title?.original}
        </div>
        <div style={{ 
          fontSize: '14px',
          color: '#4CAF50',
          marginBottom: '8px'
        }}>
          {typeof item.price?.eur === 'number' ? `${item.price.eur} €` : 'Negotiable'}
        </div>
        <div style={{ 
          fontSize: '12px',
          color: '#aaa',
          marginBottom: '4px'
        }}>
          <span style={{ 
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            padding: '2px 6px',
            borderRadius: '4px',
            marginRight: '8px',
            textTransform: 'capitalize',
            display: 'inline-flex',
            alignItems: 'center'
          }}>
            {item.source}&nbsp;
            {getFlagComponent(item.source)}
          </span>
          {item.timestamp ? new Date(item.timestamp).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }) : 'No date'}
        </div>
      </div>
    </div>
  );
} 