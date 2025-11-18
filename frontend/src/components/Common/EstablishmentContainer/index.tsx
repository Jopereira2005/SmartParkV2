"use client";
import styled from "./style.module.scss";

import { FilterIcon } from '@/assets/Common/Filter';

import { Establishment } from '@/interfaces/Establishment';

import EstablishmentCard from '../EstablishmentCard';

interface EstablishmentContainerProps {
  establishments: Establishment[] | [];
}

export default function EstablishmentContainer({ establishments }: EstablishmentContainerProps) {
  return (
    <div className={ styled.establishment_container }>
      <div className={ styled.establishment_container__header }>
        <h1 className={ styled.establishment_container__header__title }>Estabelecimentos</h1>
        <FilterIcon className={ styled.establishment_container__header__icon } />
      </div>
      <div className={ styled.establishment_container__body }>
        { establishments.length != 0 ? (
          establishments.map((establishment) => (
            <EstablishmentCard
              key={ establishment.id_establishment }
              establishment={ establishment }
              isSaved={ false }
            />
          ))) : (
          <p className={ styled.establishment_container__body__empty }>Nenhum estabelecimento encontrado.</p>
        )}
      </div>
    </div>
  );
};