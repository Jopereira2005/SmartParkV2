"use client";
import { useEffect, useState, useRef } from 'react';
import Image from 'next/image'
import Link from 'next/link';

import styled from "./style.module.scss";

import SearchBarItem from "@/components/Establishment/SearchBarItem";

import { Lot } from '@/interfaces/Lot';
import { Slot } from '@/interfaces/Slot';
import { SlotType } from '@/interfaces/SlotType';

import { SearchIcon } from '@/assets/Common/Search';

interface HeaderProps {
  lots: Lot[] | [];
  slots: Slot[] | [];
}

export default function Header({ lots, slots }: HeaderProps) {
  const [isOpen, setIsOpen] = useState(false);

  const [filteredList, setFilteredList] = useState<Slot[]>([]);
    const [inputValue, setInputValue] = useState('');
  
    const listaRef = useRef<HTMLDivElement | null>(null);
  
    const handleClickOutside = (e: MouseEvent) => {
      if (listaRef.current && !listaRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setInputValue("");
      }
    };
    
    const loadItens = async () => {
      setIsOpen(true);
      // Placeholder for loading items logic
    }
  
    useEffect(() => {
      const search = inputValue.toLowerCase().trim();

      const filtered = slots
        .filter((item) => {
          const slotName = item.slot_code.toLowerCase().trim();

          const lot = lots.find(l => l.id_lot == item.id_lot);
          const lotName = lot?.name.toLowerCase().trim() ?? "";

          return (
            slotName.includes(search) || lotName.includes(search)
          );
        })
        .sort((a, b) => Number(a.status) - Number(b.status)); // prioriza disponíveis

      setFilteredList(filtered);
    }, [inputValue]);
  
    useEffect(() => {
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, []);

  return (
    <>
      <header className={ styled.header }>
        <Link href='/' className={ styled.header__logo }>
            <Image
              className={ styled.main__welcome__image }
              src="/logo.svg"
              alt="Logo"
              width={45}
              height={35}
            />
          <h1 className={ `${isOpen ? styled.header__logo__text_open : styled.header__logo__text}` }>Smart<span>Park</span></h1>
        </Link> 
        <div className={ `${styled.header__search_bar} ${isOpen ? styled.header__search_bar__open : ''}` } ref={ listaRef }>
          <div className={ `${ styled.header__search_bar__container } ${isOpen ? styled.header__search_bar__container__open : ''}` }>
            <SearchIcon className={ styled.header__search_bar__container__icon }/>
            <input onFocus={ loadItens } className={ styled.header__search_bar__container__input }
              id="search"
              type="text" 
              placeholder="Buscar Vaga..."
              value={ inputValue }
              onChange={ (e) => setInputValue(e.target.value) }
              autoComplete="off"
            />
          </div>
          { inputValue != '' && 
            <ul className={ styled.header__search_bar__list } >
              { filteredList.length !== 0 ? 
                filteredList.map((slot) => (
                  <SearchBarItem
                    key={ slot.id_slot }
                    slot={ slot }
                    lots={ lots }
                  />
                )) :
                <span className={ styled.search_bar__list__message }>Nenhum resultado encontrado</span>
              }
            </ul>
          }
        </div>
      </header>
      {/* <Sidebar isOpen={isOpen} toggleSidebar={toggleSidebar}/> */}
    </>
  )
};