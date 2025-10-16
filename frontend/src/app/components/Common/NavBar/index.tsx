"use client";
import styled from "./style.module.scss";

interface NavBarProps {
  maxParkingSpots: number;
  occupiedSpots: number;
}
const NavBar = ({ maxParkingSpots, occupiedSpots }: NavBarProps) => {

  return (
    <div className={ styled.nav_bar }>
      <p className={ styled.nav_bar__text }>Vagas<br/>{ occupiedSpots }/{ maxParkingSpots }</p>
    </div>
  );
};
export default NavBar;