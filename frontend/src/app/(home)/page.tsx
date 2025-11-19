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

import homeService from '@/services/establishmentService';

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

  const address: Address = {
    id: "1",
    street: "R.Smart Park", 
    number: "98", 
    neighborhood: "Conj. Hab Eng da Computação", 
    country: "Brasil",
    city: "Sorocaba", 
    state: "SP", 
    postal_code: "18085-784" 
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
          isLogged={ isLogged }
        />
      </div>
      <NavBar />
    </div>
  );
}
