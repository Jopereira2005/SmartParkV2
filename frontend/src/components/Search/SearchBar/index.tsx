"use client";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from 'react';

import styled from "./style.module.scss";

import { SearchIcon } from '@/assets/Common/Search';

import { Establishment } from '@/interfaces/Establishment';

import SearchBarItem from "@/components/Search/SearchBarItem";

import establishmentService from "@/services/establishmentService";

interface SearchBarProps {
  isLogged: boolean;
}

export default function SearchBar({ isLogged }: SearchBarProps) {
  const pathname = usePathname();
  const [filteredList, setFilteredList] = useState<Establishment[]>([]);
  const [inputValue, setInputValue] = useState('');

  const listaRef = useRef<HTMLDivElement | null>(null);

  const [establishments, setEstablishments] = useState<Establishment[] | []>([]);
  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error' });
  const [alertOpen, setAlertOpen] = useState(false)

  async function loadEstablishments() {
    try {
      const data = await establishmentService.list_establishments();

      if(!data) {
        throw data.error;
      }

      setEstablishments(data);
    } catch {
      setEstablishments([]);
      setAlertProps({ message: 'Erro ao carregar estabelecimentos.', timeDuration: 3000, type: 'error' });
      setAlertOpen(true);
    }
  }

  useEffect(() => {
    if(pathname === "/search") {
      loadEstablishments();
    }
    const interval = setInterval(loadEstablishments, 15000);
    return () => clearInterval(interval);
  }, []);

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
        <input onFocus={ loadEstablishments } className={ styled.search_bar__container__input } 
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
                key={ establishment.id }
                establishment={ establishment }
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