import { ref, onMounted, onUnmounted } from 'vue';

export function useConnectivity() {
  const isOnline = ref(navigator.onLine);
  
  const updateOnlineStatus = () => {
    isOnline.value = navigator.onLine;
    console.log(isOnline.value ? '🌐 Online' : '🔌 Offline');
  };

  onMounted(() => {
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
  });

  onUnmounted(() => {
    window.removeEventListener('online', updateOnlineStatus);
    window.removeEventListener('offline', updateOnlineStatus);
  });

  return { isOnline };
}