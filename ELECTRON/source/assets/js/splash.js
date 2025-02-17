// splash.js
document.addEventListener('DOMContentLoaded', () => {
  const splashScreen = document.querySelector('.splash-screen');
  const loadingBar = document.querySelector('.splash-loading-bar');

  // Create or select the progress text element
  let progressText = document.querySelector('.splash-progress-text');
  if (!progressText) {
    progressText = document.createElement('div');
    progressText.classList.add('splash-progress-text');
    splashScreen.appendChild(progressText);
  }

  window.electronAPI.onModelPullProgress((progress) => {
    loadingBar.style.width = `${progress}%`;
    progressText.textContent = `Pulling necessary dependencies. Please wait... ${progress}%`;
  });  

  window.electronAPI.onModelPullDone(() => {
    splashScreen.classList.add('hidden');
    setTimeout(() => {
      splashScreen.style.display = 'none';
    }, 500);
  });
});
