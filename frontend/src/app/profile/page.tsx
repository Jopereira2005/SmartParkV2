"use server";
import Image from "next/image";
import styled from "./style.module.scss";

import WelcomeCard from '@/components/Common/WelcomeCard'
import CategoryCarousel from '@/components/Home/HomeCategoryCarousel'
import EstablishmentContainer from '@/components/Common/EstablishmentContainer'

import NavBar from '@/components/Common/NavBar';

import { Address } from '@/interfaces/Address';
import { Category } from '@/interfaces/Category';
import { Establishment } from '@/interfaces/Establishment';

import { ArrowIcon } from '@/assets/Common/Arrow';

import { getUser } from '@/lib/auth/getUser';

export default async function ProfilePage() {
  const { isLogged, user } = await getUser();

  const address: Address = {
    id: "1",
    street: "R.Smart Park", 
    number: "98", 
    neighborhood: "Conj. Hab Eng da Computação", 
    country: "Brasil",
    city: "Sorocaba", 
    state: "SP", 
    postal_code: "18085-784" 
  }

  return (
    <div className={ styled.home }>
      <div className={ styled.main }>
        <WelcomeCard 
          User={ user } 
          Address={ address || null} 
          isLogged={ isLogged } 
        />
      </div>
      <NavBar />
    </div>
  );
}
