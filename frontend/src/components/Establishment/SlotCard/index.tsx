"use client";
import Image from "next/image";

import styled from "./style.module.scss";

import ParkCounter from "@/components/Common/ParkCounter";

import { Slot } from '@/interfaces/Slot';
import { SlotType } from '@/interfaces/SlotType';

interface SlotCardProps {
  slot: Slot;
  slotTypes: SlotType[];
}

export default function SlotCard({ slot, slotTypes }: SlotCardProps) {
  return (
    <div className={ styled.slot_card  }>
      <div className={ styled.slot_card__info }>
        <h1 className={ styled.slot_card__info__name }>Vaga: { slot.slot_code }</h1>
        <h2 className={ styled.slot_card__info__type }>Tipo: { slotTypes.find(slotType => slotType.id_slot_type == slot.id_slot_type)?.name }</h2>
      </div>
      <div className={ styled.slot_card__status }>
        <h2 className={ `${styled.slot_card__status__text} ${ !slot.status ? styled.slot_card__status__text__ocupped : '' }` }>{ slot.status ? "Disponível" : "Ocupado" }</h2>
        <div className={ `${styled.slot_card__status__icon} ${ !slot.status ? styled.slot_card__status__icon__ocupped : '' }` }></div>
      </div>
    </div>
  );
};