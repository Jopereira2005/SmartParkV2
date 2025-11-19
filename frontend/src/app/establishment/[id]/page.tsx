"use server"
import Image from "next/image";

import styled from "./style.module.scss";

import NavBar from '@/components/Common/NavBar';
import Header from '@/components/Establishment/Header';
import ParkContainer from "@/components/Establishment/ParkContainer";

import { Lot } from '@/interfaces/Lot';
import { Slot } from '@/interfaces/Slot';
import { SlotType } from '@/interfaces/SlotType';
import { Establishment } from '@/interfaces/Establishment';

import { ArrowIcon } from '@/assets/Common/Arrow';
import { MarkIcon } from '@/assets/Common/Mark';

import { getUser } from '@/lib/auth/getUser';

import homeService from '@/services/establishmentService';

export default async function EstablishmentPage({ params }: { params: { id: string } }) {
  const { isLogged, user } = await getUser();
  const { id } = await params;


  try {
    const establishment: any = await homeService.get_establishment_info(id);

  } catch (error) {
    console.error("Erro ao carregar os dados do estabelecimento:", error);
    
  }

  const slotTypes: SlotType[] = [
    { id_slot_type: "1", name: "Normal" },
    { id_slot_type: "2", name: "Deficiente" },
    { id_slot_type: "3", name: "Idoso" },
    { id_slot_type: "4", name: "Elétrico" },
    { id_slot_type: "5", name: "Motocicleta" }
  ];

  const lots: Lot[] = [
    { id_lot: "1", id_establishment: "1", name: "Secção A" },
    { id_lot: "2", id_establishment: "1", name: "Secção B" },
    { id_lot: "3", id_establishment: "1", name: "Secção C" },
    { id_lot: "4", id_establishment: "1", name: "Secção D" },
    { id_lot: "5", id_establishment: "1", name: "Secção E" },
  ];

  const slots: Slot[] = [
    { id_slot: "1", id_lot: "1", slot_code: "A01", id_slot_type: "5", status: true },
    { id_slot: "2", id_lot: "1", slot_code: "A02", id_slot_type: "2", status: true },
    { id_slot: "3", id_lot: "1", slot_code: "A03", id_slot_type: "1", status: false },
    { id_slot: "4", id_lot: "1", slot_code: "A04", id_slot_type: "1", status: true },
    { id_slot: "5", id_lot: "1", slot_code: "A05", id_slot_type: "1", status: true },
    { id_slot: "6", id_lot: "2", slot_code: "B01", id_slot_type: "4", status: true },
    { id_slot: "7", id_lot: "2", slot_code: "B02", id_slot_type: "1", status: true },
    { id_slot: "8", id_lot: "2", slot_code: "B03", id_slot_type: "1", status: true },
    { id_slot: "9", id_lot: "2", slot_code: "B04", id_slot_type: "3", status: true },
    { id_slot: "10", id_lot: "2", slot_code: "B05", id_slot_type: "1", status: false },
    { id_slot: "11", id_lot: "3", slot_code: "C01", id_slot_type: "1", status: true },
    { id_slot: "12", id_lot: "3", slot_code: "C02", id_slot_type: "1", status: false },
    { id_slot: "13", id_lot: "3", slot_code: "C03", id_slot_type: "1", status: false },
    { id_slot: "14", id_lot: "3", slot_code: "C04", id_slot_type: "1", status: true },
    { id_slot: "15", id_lot: "3", slot_code: "C05", id_slot_type: "1", status: true },
    { id_slot: "16", id_lot: "4", slot_code: "D01", id_slot_type: "1", status: false },
    { id_slot: "17", id_lot: "4", slot_code: "D02", id_slot_type: "2", status: true },
    { id_slot: "18", id_lot: "4", slot_code: "D03", id_slot_type: "1", status: true },
    { id_slot: "19", id_lot: "4", slot_code: "D04", id_slot_type: "1", status: false },
    { id_slot: "20", id_lot: "4", slot_code: "D05", id_slot_type: "5", status: false },
    { id_slot: "21", id_lot: "5", slot_code: "E01", id_slot_type: "1", status: false },
    { id_slot: "22", id_lot: "5", slot_code: "E02", id_slot_type: "7", status: true },
    { id_slot: "23", id_lot: "5", slot_code: "E03", id_slot_type: "1", status: true },
    { id_slot: "24", id_lot: "5", slot_code: "E04", id_slot_type: "2", status: true },
    { id_slot: "25", id_lot: "5", slot_code: "E05", id_slot_type: "1", status: false },
  ];

  const establishments: Establishment = {
    name: "Facens", 
    description: "Faculdade de Engenharia de Sorocaba", 
    phone_number: "(15) 3232-3232",
    address: { 
      street: "Rodovia Senador José Ermírio de Moraes", 
      number: "1425",
      neighborhood: "Jardim Constantino Matucci", 
      country: "Brasil",
      city: "Sorocaba", 
      state: "SP", 
      postal_code: "18085-784" 
    },
  };
  
  return (
    <div className={ styled.establishment }>
      <Header id_establishment={ id } />
      <div className={ styled.main }>
        <div className={ styled.main__establishment_info }>
          <div className={ styled.main__establishment_info__banner }>
            <Image className={ styled.main__establishment_info__banner__img }
              src="/images/Banner.png" 
              alt="Banner" 
              fill
              priority
              sizes="100vw"
            />
          </div>
          <Image className={ styled.main__establishment_info__avatar }
            src="/facens.svg" 
            alt="Avatar" 
            width={ 100 } 
            height={ 100 }
            priority
          />
          <div className={ styled.main__establishment_info__info }>
            <div className={ styled.main__establishment_info__info__saved }>
              { isLogged && user &&
                <MarkIcon className={ styled.main__establishment_info__info__saved__icon }/>  
              }
            </div>
            <h1 className={ styled.main__establishment_info__info__name }>{ establishments.name }</h1>
            <p className={ styled.main__establishment_info__info__description }>{ establishments.description }</p>

            <div className={ styled.main__establishment_info__info__div }></div>

            <div className={ styled.main__establishment_info__info__address }>
              <div className={ styled.main__establishment_info__info__address__texts }>
                <h2 className={ styled.main__establishment_info__info__address__texts__title }>Endereço:</h2>
                <p className={ styled.main__establishment_info__info__address__texts__description }> { establishments.address?.street }, { establishments.address?.number } - { establishments.address?.neighborhood }, { establishments.address?.city } - { establishments.address?.state }, { establishments.address?.postal_code }</p>
              </div>
              <ArrowIcon className={ styled.main__establishment_info__info__address__icon }/>
            </div>

            <div className={ styled.main__establishment_info__info__div }></div>

            <div className={ styled.main__establishment_info__info__phone }>
              <div className={ styled.main__establishment_info__info__phone__texts }>
                <h2 className={ styled.main__establishment_info__info__phone__texts__title }>Telefone:</h2>
                <p className={ styled.main__establishment_info__info__phone__texts__description }>{ establishments.phone_number }</p>
              </div>
              <ArrowIcon className={ styled.main__establishment_info__info__address__icon }/>
            </div>

            <div className={ styled.main__establishment_info__info__div }></div>
            <h2 className={ styled.main__establishment_info__info__read_more }>Ver mais</h2>
          </div>
        </div>
        <ParkContainer id_establishment={ id } />
      </div>
      <NavBar />
    </div>
  )
}
