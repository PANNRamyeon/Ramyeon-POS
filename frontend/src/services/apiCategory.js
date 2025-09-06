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
      const response = await api.get('/category/display/');
      const data = this.handleResponse(response);
      
      return this.transformCategories(data.categories);
    } catch (error) {
      this.handleError(error);
    }
  }
  
  async getCategories() {
    try {
      const response = await api.get('/category/');
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
      .map(category => ({
        id: category._id,
        name: category.category_name,
        description: category.description,
        icon: this.mapCategoryIcon(category.category_name),
        isCustom: false,
        hasSubcategories: this.hasValidSubcategories(category.sub_categories),
        subcategories: this.transformSubcategories(category.sub_categories || []),
        // Sales data (if available)
        totalSales: category.total_sales || 0,
        totalQuantity: category.total_quantity || 0,
        subcategoryCount: category.subcategory_count || 0,
        // Raw data for reference
        rawData: category
      }));
  }

  // Transform subcategories
  transformSubcategories(subcategories) {
    if (!Array.isArray(subcategories)) {
      return [];
    }

    return subcategories
      .filter(sub => sub.name !== "None" && sub.products?.length > 0)
      .map(sub => ({
        id: this.generateSubcategoryId(sub.name),
        name: sub.name,
        products: sub.products || [],
        productCount: sub.products?.length || 0,
        // Sales data (if available)
        quantitySold: sub.quantity_sold || 0,
        totalSales: sub.total_sales || 0
      }));
  }

  // Check if category has valid subcategories
  hasValidSubcategories(subcategories) {
    if (!Array.isArray(subcategories)) return false;
    
    return subcategories.some(sub => 
      sub.name !== "None" && sub.products?.length > 0
    );
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

// Create and export singleton instance
const categoryAPIService = new CategoryAPIService();

export default categoryAPIService;