"use server";
import Image from "next/image";
import styled from "./style.module.scss";

import WelcomeCard from '@/components/Common/WelcomeCard'
import CategoryCarousel from '@/components/Home/HomeCategoryCarousel'
import EstablishmentContainer from '@/components/Common/EstablishmentContainer'

import NavBar from '@/components/Common/NavBar';

import { Address } from '@/interfaces/Address';
import { Category } from '@/interfaces/Category';
import { Establishment } from '@/interfaces/Establishment';

import { ArrowIcon } from '@/assets/Common/Arrow';

import { getUser } from '@/lib/auth/getUser';

export default async function HomePage() {
  const { isLogged, user } = await getUser();

  const categories: Category[] = [
    { id_category: "1", name: "Estacionamentos", image: "/images/Estacionamento.png" },
    { id_category: "2", name: "Supermercados", image: "/images/Supermercado.png" },
    { id_category: "3", name: "Restaurantes", image: "/images/Restaurante.png" },
    { id_category: "4", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "5", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "6", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "7", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "8", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "9", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "10", name: "Escolas", image: "/images/Escola.png" },
    { id_category: "11", name: "Escolas", image: "/images/Escola.png" },
  ];

  const establishments: Establishment[] = [
    { id_establishment: "1", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } },
    { id_establishment: "2", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } },
    { id_establishment: "3", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } },
    { id_establishment: "4", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } },
    { id_establishment: "5", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } },
    { id_establishment: "6", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: { address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" } }
  ];

  const address: Address = {
    id_address: "1",
    address: "R.Smart Park, 98", 
    district: "Conj. Hab Eng da Computação", 
    city: "Sorocaba", 
    state: "SP", 
    cep: "18085-784" 
  }

  return (
    <div className={ styled.home }>
      <div className={ styled.main }>
        <WelcomeCard 
          User={ user } 
          Address={ address || null} 
          isLogged={ isLogged } 
        />
        <div className={ styled.main__categories }>
          <h1 className={ styled.main__categories__title }>Categoria</h1>
          <CategoryCarousel
            categories={ categories }
          />
        </div>
        <EstablishmentContainer
          establishments={ establishments }
          isLogged={ isLogged }
        />
      </div>
      <NavBar />
    </div>
  );
}
