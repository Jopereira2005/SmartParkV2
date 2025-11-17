import { Address } from "./Address";

export interface Establishment {
  id_establishment?: string;
  name: string;
  description?: string;
  phone_number?: string;
  id_address?: string;
  id_category?: string;
  avatar?: string;
  background?: string;
  address?: Address;
}