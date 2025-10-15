"use client";
import Image from "next/image";
import styles from "./page.module.scss";

import CategoryCarousel from './components/Home/CategoryCarousel'

import { Category } from './interfaces/Category';

import { ArrowIcon } from './assets/Common/Arrow';

export default function Home() {
  const categories: Category[] = [
    { id_category: "1", name: "Estacionamentos", image: "/images/Estacionamento.png" },
    { id_category: "2", name: "Supermercados", image: "/images/Supermercado.png" },
    { id_category: "3", name: "Restaurantes", image: "/images/Restaurante.png" },
    { id_category: "4", name: "Escolas", image: "/images/Escola.png" },
  ];

  return (
    <div className={ styles.home }>
      <div className={ styles.main }>
        <div className={ styles.main__welcome }>
          <div className={ styles.main__welcome__image }>
            <Image 
              src="/images/Avatar.png" 
              alt="Avatar" 
              width={90} 
              height={90}
            />
          </div>

          <div className={ styles.main__welcome__texts }>
            <h1 className={ styles.main__welcome__texts__title }>Bem Vindo, Mr Paxe 👋</h1>
            <div className={ styles.main__welcome__texts__div }></div>
            <div className={ styles.main__welcome__texts__address_container }>
              <div className={ styles.main__welcome__texts__address_container__address }>
                <h2 className={ styles.main__welcome__texts__address_container__address__title }>R.Smart Park, 98</h2>
                <p className={ styles.main__welcome__texts__address_container__address__description }>Conj. Hab Eng da Computação - Facens, Sorocaba - SP</p>
              </div>
              <ArrowIcon className={ styles.main__welcome__texts__address_container__arrow } />
            </div>
          </div>
        </div>
        <div className={ styles.main__categories }>
          <h1 className={ styles.main__categories__title }>Categoria</h1>
          <CategoryCarousel
            categories={ categories }
            navigateFilter={() => {}}
          />
        </div>
      </div>
    </div>
  );
}
