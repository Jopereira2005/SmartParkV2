"use client";
import Image from "next/image";

import styled from "./style.module.scss";

import { MarkIcon } from '@/assets/Common/Mark';

import { Establishment } from '@/interfaces/Establishment';

import ParkCounter from "../ParkCounter";

interface EstablishmentCardProps {
  establishment: Establishment | null;
  navigateToEstablishment?: (establishment: Establishment) => void; 
  isSaved: boolean;
}

export default function EstablishmentCard({ establishment, navigateToEstablishment, isSaved }: EstablishmentCardProps) {
  return (
    <div className={ styled.establishment_card }>
      <div className={ styled.establishment_card__info }>
        <Image
          className={ styled.establishment_card__info__image }
          src="/facens.svg"
          alt="Facens"
          width={ 45 }
          height={ 45 }
        />
        <div className={ styled.establishment_card__info__texts }>
          <h2 className={ styled.establishment_card__info__texts__name }>{ establishment?.name }</h2>
          <p className={ styled.establishment_card__info__texts__address }>{ establishment?.address } - { establishment?.district }, { establishment?.city } - { establishment?.state }, { establishment?.cep }</p>
        </div>
      </div>
      <div className={ styled.establishment_card__others }>
        <ParkCounter maxParkingSpots={ 100 } occupiedSpots={ 100 }/>
        <div className={ styled.establishment_card__others__div }></div>
        <MarkIcon className={ `${ styled.establishment_card__others__icon } ${ isSaved ? styled.establishment_card__others__icon__isMarked : '' }` }/>
      </div>
    </div>
  );
};