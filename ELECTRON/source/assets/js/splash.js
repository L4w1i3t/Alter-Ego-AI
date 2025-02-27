document.addEventListener('DOMContentLoaded', () => {
    const splashScreen = document.querySelector('.splash-screen');
    const loadingBar = document.querySelector('.splash-loading-bar');
    
    // Function to update loading bar
    function updateLoadingBar(percentage) {
      loadingBar.style.width = `${percentage}%`;
    }
  
    // Function to hide splash screen
    function hideSplashScreen() {
      splashScreen.classList.add('hidden');
      // Remove from DOM after transition
      setTimeout(() => {
        splashScreen.style.display = 'none';
      }, 500);
    }
  
    // Simulate loading process using requestAnimationFrame for smoother animation
    function simulateLoading() {
      return new Promise((resolve) => {
        const totalTime = 3000; // 3 seconds total
        const startTime = performance.now();
        function update() {
          const elapsed = performance.now() - startTime;
          const progress = Math.min((elapsed / totalTime) * 100, 100);
          updateLoadingBar(progress);
          if (progress < 100) {
            requestAnimationFrame(update);
          } else {
            resolve();
          }
        }
        requestAnimationFrame(update);
      });
    }
  
    // Run loading simulation and then hide splash screen
    simulateLoading().then(hideSplashScreen);
  
    // Allow manual dismissal
    // splashScreen.addEventListener('click', hideSplashScreen);
  });
  