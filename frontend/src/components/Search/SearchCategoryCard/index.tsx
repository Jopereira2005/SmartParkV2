"use client";
import Image from "next/image";

import styled from "./style.module.scss";

import { Category } from '@/interfaces/Category';

interface SearchCategoryCardProps {
  category: Category | null;
  setFilter?: (category: Category) => void; 
  isActive: boolean;
}

export default function SearchCategoryCard({ category, setFilter, isActive }: SearchCategoryCardProps) {

  return (
    <div className={ `${ styled.category_card } ${ isActive ? styled.category_card__active : '' }`  }>
      <Image
        className={ styled.category_card__image }
        src={ category?.image || "/images/Estacionamento.png" }
        alt={ category?.name || "Categoria" }
        width={ 30 }
        height={ 30 }
      />
      <h1 className={ styled.category_card__title }>{ category?.name }</h1>
    </div>
  );
};