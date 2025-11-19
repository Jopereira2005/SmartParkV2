"use client";
import { useEffect, useState } from 'react'
import styled from "./style.module.scss";

import { Lot } from '@/interfaces/Lot';
import { Slot } from '@/interfaces/Slot';
import { SlotType } from "@/interfaces/SlotType";

import SlotContainer from '../SlotContainer';
import AlertNotification from '@/components/Common/AlertNotification';

import { ReloadIcon } from '@/assets/Common/Reload';

import establishmentService from "@/services/establishmentService";

interface ParkContainerProps {
  id_establishment: string | null;
}

export default function ParkContainer({ id_establishment }: ParkContainerProps) {
  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error' });
  const [alertOpen, setAlertOpen] = useState(false)

  const [slotTypes, setSlotTypes] = useState<SlotType[]>([]);
  const [lots, setLots] = useState<Lot[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  
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
      const slotTypesConvertedMap: Record<string, SlotType> = {}; // evita duplicados

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

          // registra SlotType (sem duplicar)
          if (!slotTypesConvertedMap[slotData.slot_type]) {
            slotTypesConvertedMap[slotData.slot_type] = {
              id_slot_type: slotData.slot_type,
              name: slotData.slot_type
            };
          }
        });
      });

      // SlotTypes em array final
      const slotTypesConverted = Object.values(slotTypesConvertedMap);

      /* ============================================================
          Atualizando states
      ============================================================ */
      setLots(lotsConverted);
      setSlots(slotsConverted);
      setSlotTypes(slotTypesConverted);

    } catch (error) {
      console.log(error);
      setLots([]);
      setSlots([]);
      setSlotTypes([]);

      setAlertProps({
        message: 'Erro ao carregar estabelecimentos.',
        timeDuration: 3000,
        type: 'error'
      });
      setAlertOpen(true);
    }
  }

  useEffect(() => {
    loadPark();
    const interval = setInterval(loadPark, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <div className={ styled.park_container }>
        <div className={ styled.park_container__header }>
          <h1 className={ styled.park_container__header__title }>Vagas</h1>
          <ReloadIcon className={ styled.park_container__header__icon } />
        </div>

        <div className={ styled.park_container__body }>
          { lots.map((lot) => (
            <SlotContainer
              key={ lot.id_lot }
              lot={ lot }
              slots={ slots }
              slotTypes={ slotTypes }
            />
          ))}
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