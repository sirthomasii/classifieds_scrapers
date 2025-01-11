import Papa from 'papaparse';

self.addEventListener('message', (event) => {
  const { csvString } = event.data;
  
  const points: { x: number; y: number; z: number; value: number }[] = [];
  let minValue = Infinity;
  let maxValue = -Infinity;

  Papa.parse(csvString, {
    step: (results: Papa.ParseResult<string[]>) => {
      const [x, y, z, value] = results.data.map(Number);
      if (!isNaN(x) && isFinite(x) &&
          !isNaN(y) && isFinite(y) &&
          !isNaN(z) && isFinite(z) &&
          !isNaN(value) && isFinite(value)) {
        points.push({ x, y, z, value });
        minValue = Math.min(minValue, value);
        maxValue = Math.max(maxValue, value);
      }
    },
    complete: () => {
      self.postMessage({ points, minValue, maxValue });
    },
    error: (error) => {
      self.postMessage({ error: error.message });
    }
  });
});