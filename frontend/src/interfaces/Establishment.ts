import { Address } from "./Address";

export interface Establishment {
  id?: string;
  name: string;
  description?: string;
  phone_number?: string;
  address?: Address;
}