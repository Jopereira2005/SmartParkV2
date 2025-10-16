"use client";
import Image from "next/image";
import styled from "./page.module.scss";

import CategoryCarousel from './components/Home/CategoryCarousel'
import EstablishmentContainer from './components/Common/EstablishmentContainer'

import { Category } from './interfaces/Category';
import { Establishment } from './interfaces/Establishment';

import { ArrowIcon } from './assets/Common/Arrow';

export default function Home() {
  const categories: Category[] = [
    { id_category: "1", name: "Estacionamentos", image: "/images/Estacionamento.png" },
    { id_category: "2", name: "Supermercados", image: "/images/Supermercado.png" },
    { id_category: "3", name: "Restaurantes", image: "/images/Restaurante.png" },
    { id_category: "4", name: "Escolas", image: "/images/Escola.png" },
  ];

  const establishments: Establishment[] = [
    { id_establishment: "1", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "2", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "3", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "4", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "5", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" },
    { id_establishment: "6", public_id: "abc123", name: "Facens", description: "Faculdade de Engenharia de Sorocaba", address: "Rodovia Senador José Ermírio de Moraes, 1425", district: "Jardim Constantino Matucci", city: "Sorocaba", state: "SP", cep: "18085-784" }
  ]

  return (
    <div className={ styled.home }>
      <div className={ styled.main }>
        <div className={ styled.main__welcome }>
          <div className={ styled.main__welcome__image }>
            <Image 
              src="/images/Avatar.png" 
              alt="Avatar" 
              width={90} 
              height={90}
            />
          </div>

          <div className={ styled.main__welcome__texts }>
            <h1 className={ styled.main__welcome__texts__title }>Bem Vindo, Mr Paxe 👋</h1>
            <div className={ styled.main__welcome__texts__div }></div>
            <div className={ styled.main__welcome__texts__address_container }>
              <div className={ styled.main__welcome__texts__address_container__address }>
                <h2 className={ styled.main__welcome__texts__address_container__address__title }>R.Smart Park, 98</h2>
                <p className={ styled.main__welcome__texts__address_container__address__description }>Conj. Hab Eng da Computação - Facens, Sorocaba - SP</p>
              </div>
              <ArrowIcon className={ styled.main__welcome__texts__address_container__arrow } />
            </div>
          </div>
        </div>
        <div className={ styled.main__categories }>
          <h1 className={ styled.main__categories__title }>Categoria</h1>
          <CategoryCarousel
            categories={ categories }
            navigateFilter={() => {}}
          />
        </div>
        <EstablishmentContainer
          establishments={ establishments }
          navigateToEstablishment={() => {}}
        />
      </div>
    </div>
  );
}
