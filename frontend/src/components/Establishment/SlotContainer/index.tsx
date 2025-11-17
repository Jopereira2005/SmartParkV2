"use client";
import { useState } from 'react'
import styled from "./style.module.scss";

import SlotCard from "@/components/Establishment/SlotCard";

import { Lot } from '@/interfaces/Lot';
import { Slot } from '@/interfaces/Slot';
import { SlotType } from "@/interfaces/SlotType";

import { ArrowIcon } from '@/assets/Common/Arrow';

interface SlotContainerProps {
  lot: Lot;
  slots: Slot[] | [];
  slotTypes: SlotType[] | [];
}

export default function SlotContainer({ lot, slots, slotTypes }: SlotContainerProps) {
 const [openId, setOpenId] = useState<string | null>(null);

  const toggle = (id_slot: string) => {
    setOpenId(prev => (prev === id_slot ? null : id_slot));
  };

  return (
    <div id={ lot.id_lot } className={ styled.slot_container }>
      <div className={ styled.slot_container__header } onClick={ () => toggle(lot.name) }>
        <h1 className={ `${ styled.slot_container__header__title } ${ openId == lot.name ? styled.slot_container__header__title__open : '' }` }>{ lot.name }</h1>
        <ArrowIcon className={ `${ styled.slot_container__header__icon } ${ openId == lot.name ? styled.slot_container__header__icon__open : '' }` } />  
      </div>

      <div className={ `${ styled.slot_container__content } ${ openId == lot.name ? styled.slot_container__content__open : '' }` }>
        <div className={ `${ styled.slot_container__content__container } ${ openId == lot.name ? styled.slot_container__content__container__open : '' }` }>
          { 
            slots.filter(slot => slot.id_lot == lot.id_lot).map((slot) => (
              <SlotCard key={ slot.id_slot } slot={ slot } slotTypes={ slotTypes } />
            ))
          }
        </div>
      </div>
    </div>
  );
};