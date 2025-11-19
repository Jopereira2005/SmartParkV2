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

import establishmentService from "@/services/establishmentService";

interface HeaderProps {
  id_establishment: string | '';
}

export default function Header({ id_establishment }: HeaderProps) {
  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error' });
  const [alertOpen, setAlertOpen] = useState(false);

  const [lots, setLots] = useState<Lot[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);

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
  
  async function loadPark() {
    try {
      const data = await establishmentService.list_establishment_by_lot(id_establishment || '');

      if (!data) {
        throw new Error("Nenhum dado retornado");
      }

      /* ============================================================
        CONVERSÃO DOS DADOS
        data.lots = { L01: {...}, L02: {...}, ... }
      ============================================================ */
      
      // LOTS
      const lotsConverted: Lot[] = Object.entries(data.lots).map(([lotCode, lotValue]: any) => ({
        id_lot: lotCode,                  // "L01"
        id_establishment: data.establishment_id?.toString(),
        name: lotValue.lot_name,          // "Piso 1"
        lot_code: lotCode                 // "L01"
      }));

      // SLOTS
      const slotsConverted: Slot[] = [];

      Object.entries(data.lots).forEach(([lotCode, lotValue]: any) => {
        Object.entries(lotValue.slots).forEach(([slotCode, slotData]: any) => {
          // monta os slots
          slotsConverted.push({
            id_slot: slotCode,          // "V001"
            id_lot: lotCode,            // "L01"
            slot_code: slotCode,        // "V001"
            id_slot_type: slotData.slot_type,  
            status: slotData.status === "FREE"
          });
        });
      });


      /* ============================================================
          Atualizando states
      ============================================================ */
      setLots(lotsConverted);
      setSlots(slotsConverted);

    } catch (error) {
      console.log(error);
      setLots([]);
      setSlots([]);

      setAlertProps({
        message: 'Erro ao carregar estabelecimentos.',
        timeDuration: 3000,
        type: 'error'
      });
      setAlertOpen(true);
    }
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
    loadPark();
    const interval = setInterval(loadPark, 15000);
    return () => clearInterval(interval);
  }, []);

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
            <input onFocus={ loadPark } className={ styled.header__search_bar__container__input }
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
                filteredList.map((slot, index) => (
                  <SearchBarItem
                    key={ `${slot.slot_code}-${index}` }
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