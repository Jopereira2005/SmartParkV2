"use client";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import styled from "./style.module.scss";

import { FilterIcon } from '@/assets/Common/Filter';

import { Establishment } from '@/interfaces/Establishment';

import EstablishmentCard from '../EstablishmentCard';
import AlertNotification from "@/components/Common/AlertNotification";

import establishmentService from "@/services/establishmentService";


interface EstablishmentContainerProps {
  isLogged?: boolean;
}

export default function EstablishmentContainer({ isLogged }: EstablishmentContainerProps) {
  const pathname = usePathname();

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
    if(pathname === "/"  || pathname === "/search") {
      loadEstablishments();
    }
    const interval = setInterval(loadEstablishments, 1000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <>
      <div className={ styled.establishment_container }>
        <div className={ styled.establishment_container__header }>
          <h1 className={ styled.establishment_container__header__title }>Estabelecimentos</h1>
          <FilterIcon className={ styled.establishment_container__header__icon } />
        </div>
        <div className={ styled.establishment_container__body }>
          { establishments.length != 0  ? (
            establishments.map((establishment) => (
              <EstablishmentCard
                key={ establishment.id }
                establishment={ establishment }
                isSaved={ false }
                isLogged={ isLogged }
              />
            ))) : (
            <p className={ styled.establishment_container__body__empty }>Nenhum estabelecimento encontrado.</p>
          )}
        </div>
      </div>
      <AlertNotification
        {...alertProps}
        state={ alertOpen }
        handleClose={() => setAlertOpen(false)}      
      />
    </>
  );
};