"use client";
import Image from "next/image";

import styled from "./style.module.scss";

import { Establishment } from '@/interfaces/Establishment';

import { MarkIcon } from '@/assets/Common/Mark';

import ParkCounter from "@/components/Common/ParkCounter";

interface SearchBarItemProps {
  establishment: Establishment | null;
  isSaved: boolean;
}

export default function SearchBarItem({ establishment, isSaved }: SearchBarItemProps) {
  return (
    <div className={ styled.search_bar_item  }>
      <div className={ styled.search_bar_item__info }>
        <Image
          className={ styled.search_bar_item__info__image }
          src="/facens.svg"
          alt="Facens"
          width={ 30 }
          height={ 30 }
        />
        <div className={ styled.search_bar_item__info__texts }>
          <h2 className={ styled.search_bar_item__info__texts__name }>{ establishment?.name }</h2>
          <p className={ styled.search_bar_item__info__texts__address }>| { establishment?.address?.street }, { establishment?.address?.number } - { establishment?.address?.neighborhood }, { establishment?.address?.city } - { establishment?.address?.state }, { establishment?.address?.postal_code }</p>
        </div>
      </div>
      <div className={ styled.search_bar_item__others }>
        <ParkCounter maxParkingSpots={ 100 } occupiedSpots={ 100 }/>
        <div className={ styled.search_bar_item__others__div }></div>
        <MarkIcon className={ `${ styled.search_bar_item__others__icon } ${ isSaved ? styled.search_bar_item__others__icon__isMarked : '' }` }/>
      </div>
    </div>
  );
};