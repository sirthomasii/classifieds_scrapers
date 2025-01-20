import { GB, DK, FI, CH, DE, RO, SE } from 'country-flag-icons/react/3x2';

export const getFlagComponent = (source: string) => {
  switch(source) {
    case 'ricardo':
      return <CH style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'gumtree':
      return <GB style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'kleinanzeigen':
      return <DE style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'olx':
      return <RO style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'blocket':
      return <SE style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'tori':
      return <FI style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    case 'dba':
      return <DK style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
    default:
      return null;
  }
}; 