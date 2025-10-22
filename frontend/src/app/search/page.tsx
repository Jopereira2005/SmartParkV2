"use client";
import Image from "next/image";
import styled from "./style.module.scss";

import NavBar from '@/components/Common/NavBar';
import EstablishmentContainer from '@/components/Common/EstablishmentContainer'
import CategoryCarousel from '@/components/Search/SearchCategoryCarousel';
import SearchBar from '@/components/Search/SearchBar';

import { Category } from '@/interfaces/Category';
import { Establishment } from '@/interfaces/Establishment';

import { ArrowIcon } from '@/assets/Common/Arrow';

export default function Search() {
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

  const establishments: Establishment[] = [
    { id_establishment: "1", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "2", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "3", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "4", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "5", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "6", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" }
  ];

  return (
    <div className={ styled.home }>
      <div className={ styled.main }>
        <SearchBar 
          establishments={ establishments }
          navigateTo={ (establishment) => console.log(establishment) }
          loadItens={ () => Promise.resolve() }
          saveFunction={ (establishment) => console.log(establishment) }
        />
        <div className={ styled.main__categories }>
          <h1 className={ styled.main__categories__title }>Categorias</h1>
          <CategoryCarousel categories={ categories } />
        </div>
        <EstablishmentContainer establishments={ establishments } />
      </div>
      <NavBar />
    </div>
  );
}
