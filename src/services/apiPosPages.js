import { api } from './api.js'

class PosPageAPIService {
  async getPages() {
    const response = await api.get('/admin/pos-pages/')
    return response.data.pages || []
  }

  async createPage(pageName, icon) {
    const response = await api.post('/admin/pos-pages/', { page_name: pageName, icon })
    return response.data.page
  }

  async updatePage(pageId, updates) {
    const response = await api.put(`/admin/pos-pages/${pageId}/`, updates)
    return response.data.page
  }

  async deletePage(pageId) {
    await api.delete(`/admin/pos-pages/${pageId}/`)
  }

  async addProducts(pageId, productIds) {
    const response = await api.post(`/admin/pos-pages/${pageId}/products/`, { product_ids: productIds })
    return response.data.page
  }

  async removeProducts(pageId, productIds) {
    const response = await api.delete(`/admin/pos-pages/${pageId}/products/`, {
      data: { product_ids: productIds }
    })
    return response.data.page
  }
}

export default new PosPageAPIService()
