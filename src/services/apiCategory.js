import { api } from './api.js';

class CategoryAPIService {
  // Helper method to handle responses
  handleResponse(response) {
    return response.data;
  }

  // Helper method to handle errors
  handleError(error) {
    const message = error.response?.data?.error || 
                   error.response?.data?.message || 
                   error.message || 
                   'An unexpected error occurred';
    throw new Error(message);
  }

  async getActiveCategories() {
    try {
      const response = await api.get('/admin/categories/?active_only=true');
      const data = this.handleResponse(response);

      return this.transformCategories(data.categories);
    } catch (error) {
      this.handleError(error);
    }
  }

  async getCategories() {
    try {
      const response = await api.get('/admin/categories/');
      const data = this.handleResponse(response);

      return this.transformCategories(data.categories);
    } catch (error) {
      this.handleError(error);
    }
  }

  transformCategories(categories) {
    if (!Array.isArray(categories)) {
      return [];
    }

    return categories
      .filter(category => category.status === 'active' && !category.isDeleted)
      .map(category => {
        // Back office returns category_id; old backend returned _id
        const id = category.category_id || category._id
        return {
          id,
          name: category.category_name,
          description: category.description,
          icon: this.mapCategoryIcon(category.category_name),
          image: category.image_url || null,
          isCustom: false,
          hasSubcategories: this.hasValidSubcategories(category.sub_categories),
          subcategories: this.transformSubcategories(category.sub_categories || []),
          totalSales: category.total_sales || 0,
          totalQuantity: category.total_quantity || 0,
          subcategoryCount: category.subcategory_count || 0,
          rawData: category
        }
      });
  }

  // Transform subcategories
  transformSubcategories(subcategories) {
    if (!Array.isArray(subcategories)) {
      return [];
    }

    return subcategories
      // Back office doesn't embed products in subcategories — filter only by name
      .filter(sub => sub.name && sub.name !== 'None' && sub.status !== 'deleted')
      .map(sub => ({
        id: sub.subcategory_id || this.generateSubcategoryId(sub.name),
        name: sub.name,
        products: sub.products || [],
        productCount: sub.product_count || sub.products?.length || 0,
        quantitySold: sub.quantity_sold || 0,
        totalSales: sub.total_sales || 0
      }));
  }

  // Check if category has valid subcategories
  hasValidSubcategories(subcategories) {
    if (!Array.isArray(subcategories)) return false;
    return subcategories.some(sub => sub.name && sub.name !== 'None' && sub.status !== 'deleted');
  }

  // Generate consistent subcategory ID
  generateSubcategoryId(subcategoryName) {
    return `sub_${subcategoryName.replace(/\s+/g, '_').toLowerCase()}`;
  }

  // Map category names to icons
  mapCategoryIcon(categoryName) {
    const iconMap = {
      'Drinks': 'Coffee',
      'Noodles': 'Soup', 
      'Toppings': 'Package',
      'Snacks': 'ShoppingBag',
      'Desserts': 'Cake',
      'Others': 'Grid3X3',
      'Combo': 'MoreHorizontal'
    };
    return iconMap[categoryName] || 'Package';
  }
  

}

const categoryAPIService = new CategoryAPIService();

export default categoryAPIService;