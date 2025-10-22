"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from 'react';

import styled from "./style.module.scss";

import { SearchIcon } from '@/assets/Common/Search';

import { Establishment } from '@/interfaces/Establishment';

import SearchBarItem from "@/components/Search/SearchBarItem";

interface SearchBarProps {
  establishments: Establishment[];
  saveFunction?: (establishment: Establishment) => void;
  navigateTo: (id_establishment: Establishment) => void;
  loadItens: () => Promise<void>
}

export default function SearchBar({ establishments, saveFunction, navigateTo, loadItens }: SearchBarProps) {
  const [filteredList, setFilteredList] = useState<Establishment[]>([]);
  const [inputValue, setInputValue] = useState('');

  const listaRef = useRef<HTMLDivElement | null>(null);

  const handleClickOutside = (e: MouseEvent) => {
    if (listaRef.current && !listaRef.current.contains(e.target as Node)) {
      setInputValue("");
    }
  };

  useEffect(() => {
    setFilteredList( establishments.filter((item) => 
      item.name.toLowerCase().trim().includes(inputValue.toLowerCase().trim())
  ))
  }, [ inputValue ]);

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div className={ styled.search_bar } ref={ listaRef }>
      <div className={ styled.search_bar__container }>
        <SearchIcon className={ styled.search_bar__container__icon }/>
        <input onFocus={ loadItens } className={ styled.search_bar__container__input } 
          type="text" 
          placeholder="Buscar estabelecimento..."
          value={ inputValue }
          onChange={ (e) => setInputValue(e.target.value) }
        />
      </div>
      { inputValue != '' && 
        <ul className={ styled.search_bar__list } >
          { filteredList.length !== 0 ? 
            filteredList.map((establishment) => (
              <SearchBarItem
                key={ establishment.id_establishment }
                establishment={ establishment }
                saveFunction={ saveFunction }
                navigateTo={ navigateTo }
                isSaved={ false }
              />
            )) :
            <span className={ styled.search_bar__list__message }>Nenhum resultado encontrado</span>
          }
        </ul>
      }
    </div>
  );
};  