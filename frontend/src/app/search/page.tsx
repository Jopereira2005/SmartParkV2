"use server";
import Image from "next/image";

import styled from "./style.module.scss";

import NavBar from '@/components/Common/NavBar';
import EstablishmentContainer from '@/components/Common/EstablishmentContainer'
import CategoryCarousel from '@/components/Search/SearchCategoryCarousel';
import SearchBar from '@/components/Search/SearchBar';

import { Category } from '@/interfaces/Category';
import { Establishment } from '@/interfaces/Establishment';

import { ArrowIcon } from '@/assets/Common/Arrow';
import { getUser } from "@/lib/auth/getUser";

export default async function SearchPage() {
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
    { id_category: "11", name: "Escolas", image: "/images/Escola.png" }
  ];


  return (
    <div className={ styled.home }>
      <div className={ styled.main }>
        <SearchBar isLogged={ isLogged } />
        <div className={ styled.main__categories }>
          <h1 className={ styled.main__categories__title }>Categorias</h1>
          <CategoryCarousel categories={ categories } />
        </div>
        <EstablishmentContainer isLogged={ isLogged } />
      </div>
      <NavBar />
    </div>
  );
}
