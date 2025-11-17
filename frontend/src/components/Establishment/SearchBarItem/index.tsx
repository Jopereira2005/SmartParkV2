"use client";
import Image from "next/image";

import styled from "./style.module.scss";

import { Lot } from '@/interfaces/Lot';
import { Slot } from '@/interfaces/Slot';

import ParkCounter from "@/components/Common/ParkCounter";

interface LotCardProps {
  lots: Lot[];
  slot: Slot;
}

export default function LotCard({ lots, slot }: LotCardProps) {
  return (
    <div className={ styled.search_bar_item }>
      <div className={ styled.search_bar_item__info }>
        <div className={ styled.search_bar_item__info__texts }>
          <h2 className={ styled.search_bar_item__info__texts__name }>{ slot.slot_code }</h2>
          { lots.find(lot => lot.id_lot == slot.id_lot)?.name && 
            <p className={ styled.search_bar_item__info__texts__slot }>| { lots.find(lot => lot.id_lot == slot.id_lot)?.name }</p>   
          }
        </div>
      </div>
      <div className={ `${styled.search_bar_item__status} ${ slot.status ? styled.search_bar_item__status__ocupped : '' }` }>{ slot.status ? "Ocupado" : "Disponível" }</div>
    </div>
  );
};