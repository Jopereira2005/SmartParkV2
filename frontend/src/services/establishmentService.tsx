import { apiClientFetch } from "./api/client";
import { apiServerFetch } from "./api/server";

import { cookies } from "next/headers";


const establishmentService = {
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

  async list_establishment_by_lot(id_establishment: string) {
    try {
      const response = await apiClientFetch(`/catalog/public/establishments/${id_establishment}/lots/`)
      
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

  async get_establishment_info(id_establishment: string) {
    try {
      const response = await apiServerFetch(`/catalog/establishments/${id_establishment}/`)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw errorData || { error: "Erro desconhecido" };
      }

      const data = await response.json();
      return data;

    } catch (error: any) {
      return error;
    }
  }
};

export default establishmentService;