import styles from '../viewport.module.css';

export function AdCard() {
  return (
    <div className={styles.itemCard}>
      <div style={{ 
        position: 'absolute', 
        top: '8px', 
        left: '8px', 
        fontSize: '12px', 
        fontStyle: 'italic',
        color: 'rgba(255, 255, 255, 0.5)',
        zIndex: 1
      }}>
        Advertisement
      </div>
      <div style={{ width: '100%', height: '100%' }}
        dangerouslySetInnerHTML={{
          __html: `
            <!-- AD_002 -->
            <ins class="adsbygoogle"
                 style="display:block; width:100%; height:100%;"
                 data-ad-client="ca-pub-4841275450464973"
                 data-ad-slot="4182640824"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
          `
        }}
      />
    </div>
  );
} 