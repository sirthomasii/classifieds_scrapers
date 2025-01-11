import React, { useEffect, useRef } from 'react';

const MatrixBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;

    const ctx = c.getContext("2d");
    if (!ctx) return;

    // Making the canvas full screen
    c.height = window.innerHeight;
    c.width = window.innerWidth;

    // Characters to display
    const matrix = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789@#$%^&*()*&^%+-/~{[|`]}";
    const characters = matrix.split("");
    const fontSize = 10;
    const columns = c.width / fontSize; // Number of columns for the rain
    const drops = Array.from({ length: Math.floor(columns) }, () => Math.random() * c.height); // Random initial y-coordinate for each drop

    // Drawing the characters
    const draw = () => {
      // Black BG for the canvas with translucent effect
      ctx.fillStyle = "rgba(0, 0, 0, 0.04)";
      ctx.fillRect(0, 0, c.width, c.height);

      ctx.fillStyle = "#8A2BE2"; // Updated to a violet color
      ctx.font = `${fontSize}px Arial`;

      // Looping over drops
      for (let i = 0; i < drops.length; i++) {
        const text = characters[Math.floor(Math.random() * characters.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        // Resetting the drop to the top randomly after it has crossed the screen
        if (drops[i] * fontSize > c.height && Math.random() > 0.97) {
          drops[i] = 0;
        }
        drops[i] += 0.5; // Slower drop
      }
    };

    setInterval(draw, 50);
    window.addEventListener('resize', draw);

    return () => {
      window.removeEventListener('resize', draw);
    };
  }, [canvasRef]);

  return (
    <canvas 
      ref={canvasRef} 
      style={{ 
        position: 'absolute', // Positioning the canvas absolutely
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%', 
        pointerEvents: 'none' // Allow clicks to pass through the canvas
      }} 
    />
  );
};

export default MatrixBackground;