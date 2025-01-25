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

    // Simulate loading process
    function simulateLoading() {
        return new Promise((resolve) => {
            const totalTime = 3000; // 3 seconds total
            const intervals = 20; // number of updates
            const step = 100 / intervals;
            let progress = 0;

            const timer = setInterval(() => {
                progress += step;
                updateLoadingBar(progress);

                if (progress >= 100) {
                    clearInterval(timer);
                    resolve();
                }
            }, totalTime / intervals);
        });
    }

    // Run loading simulation and then hide splash screen
    simulateLoading().then(hideSplashScreen);

    // Allow manual dismissal
    //splashScreen.addEventListener('click', hideSplashScreen);
});