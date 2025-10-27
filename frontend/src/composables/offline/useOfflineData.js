import { ref, computed } from 'vue';
import { useOfflineCartStore } from '@/stores/offlineCartStores';
import apiService from '@/services/api';

export function useOfflineData() {
  const cartStore = useOfflineCartStore();
  
  const products = ref([]);
  const categories = ref([]);
  const isLoading = ref(false);

  const loadProducts = async () => {
    isLoading.value = true;
    try {
      products.value = await apiService.getProductsWithCache();
      cartStore.updateLocalStock(products.value);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const getProductStock = (productId) => {
    return cartStore.getProductStock(productId);
  };

  return {
    products,
    categories,
    isLoading,
    loadProducts,
    getProductStock
  };
}