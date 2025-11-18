"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";

import styled from "./style.module.scss";

import { User } from "@/interfaces/User";
import { Address } from "@/interfaces/Address";

import { EmailIcon } from '@/assets/Search/Email';
import { ArrowIcon } from '@/assets/Common/Arrow';

interface WelcomeCardProps {
  User: User | null; 
  Address: Address | null;
  isLogged: boolean;
}

export default function WelcomeCard({ User, Address, isLogged }: WelcomeCardProps) {
  const pathname = usePathname();

  return (
    <div className={ styled.welcome }>
      <Image
        className={ styled.welcome__image }
        src={ isLogged ? "/images/Avatar.png" : "/images/DefaultAvatar2.png" } 
        alt="Avatar" 
        width={ 90 } 
        height={ 90 }
        priority
      />
      <div className={ styled.welcome__texts }>
        <h1 className={ styled.welcome__texts__title }>Bem Vindo, { User ? User.first_name : "Visitante" } 👋</h1>
        { pathname == "/profile" && isLogged && 
          <div className={ styled.welcome__texts__email }>
            <EmailIcon className={ styled.welcome__texts__email__icon } />
            <h2 className={ styled.welcome__texts__email__text }>{ User ? User.email : "" }</h2>
          </div>
        }
        <div className={ styled.welcome__texts__div }></div>
        <div className={ styled.welcome__texts__under_bar }>
          { Address && isLogged ?
            <>
              <div className={ styled.welcome__texts__under_bar__address }>
                { pathname != "/profile" ? 
                <>
                  <h2 className={ styled.welcome__texts__under_bar__address__title }>{ Address.address }</h2>
                  <p className={ styled.welcome__texts__under_bar__address__description }>{ Address.district }, { Address.city } - { Address.state }, { Address.cep }</p>
                </> : 
                <>
                  <h2 className={ styled.welcome__texts__under_bar__address__text }>{ Address.address }<span> | { Address.district }, { Address.city } - { Address.state }, { Address.cep }</span></h2>
                </>
                }
              </div>
              { pathname != "/profile" && 
                <ArrowIcon className={ styled.welcome__texts__under_bar__arrow } />
              }
            </> :
            <div className={ styled.welcome__texts__under_bar__buttons }>
              <Link className={ styled.welcome__texts__under_bar__buttons__login } href="/login">Entrar</Link>
              <Link className={ styled.welcome__texts__under_bar__buttons__register } href="/register">Registrar</Link>
            </div>
          }
        </div>
      </div>
    </div>
  );
};