"use client";
import styled from "./style.module.scss";

import { FilterIcon } from '@/assets/Common/Filter';

interface ParkCounterProps {
  maxParkingSpots: number;
  occupiedSpots: number;
}

export default function ParkCounter({ maxParkingSpots, occupiedSpots }: ParkCounterProps) {
  return (
    <div className={ `${styled.park_counter} ${ (maxParkingSpots == occupiedSpots) ? styled.park_counter__full : '' }` }>
      <p className={ styled.park_counter__text }>Vagas</p>
      <p className={ styled.park_counter__text }>{ occupiedSpots }/{ maxParkingSpots }</p>
    </div>
  );
};