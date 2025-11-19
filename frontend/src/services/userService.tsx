import { apiClientFetch } from "./api/client";

const userService = {
  async list_establishments() {
    try {
      const response = await apiClientFetch("/catalog/public/establishments/")
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw errorData || { error: "Erro desconhecido" };
      }

      const data = await response.json();
      return data;

    } catch (error: any) {
      return error;
    }
  },
};

export default userService;