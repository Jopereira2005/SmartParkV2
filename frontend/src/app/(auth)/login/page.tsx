"use client";
import Image from "next/image";
import Link from 'next/link';
import { useRouter } from "next/navigation";
import { useState } from "react";

import styled from "../style.module.scss";

import Input from '@/components/Auth/Input';
import AlertNotification from '@/components/Common/AlertNotification';

import { FacebookIcon } from "@/assets/Auth/Facebook";
import { GoogleIcon } from "@/assets/Auth/Google";
import { TwitterIcon } from "@/assets/Auth/Twitter";

import { login } from "@/lib/auth/login";

export default function LoginPage() {
  const router = useRouter();
  
  const [credentials, setCredentials] = useState({ username: '', password: '' });

  const [alertProps, setAlertProps] = useState({ message: '', timeDuration: 0, type: 'success' as 'success' | 'error'});
  const [alertOpen, setAlertOpen] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response: any = await login(credentials);

      if(!response.ok) 
        throw response

      setAlertProps({
        message: "Login efetuado com sucesso.",
        timeDuration: 2000,
        type: 'success'     
      });
      setAlertOpen(true);

      setTimeout(() => {
        router.replace("/");
      }, 2500)
       

    } catch(err: any){ 
      setAlertProps({
        message: err.message,
        timeDuration: 2000,
        type: 'error'     
      });
      setAlertOpen(true);
    }
  };

  return (
    <div className={ styled.auth }>
      <div className={ styled.background }>
        <div className={ styled.main }>
          <div className={ styled.main__welcome }>
            <Link href='/'>
              <Image
                className={ styled.main__welcome__image }
                src="/logo.svg"
                alt="Logo"
                width={170}
                height={142}
                priority
              />
            </Link>
            <h1 className={ styled.main__welcome__text }>Bem-vindo de volta ao <span>SmartPark!</span></h1>
          </div>

          <div className={ styled.main__div }></div>

          <div className={ styled.main__auth }>
            <h1 className={ styled.main__auth__title }>Login</h1>
            <form onSubmit={ handleLogin } className={ styled.main__auth__form }>
              <div className={ styled.main__auth__form__inputs }>
                <Input
                  type="text"
                  name="username"
                  label="Nome de Usuario"
                  value={credentials.username}
                  onChangeFunc={(e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, username: e.target.value })}
                />

                <Input
                  type="password"
                  name="password"
                  label="Senha"
                  value={credentials.password}
                  onChangeFunc={(e: React.ChangeEvent<HTMLInputElement>) => setCredentials({ ...credentials, password: e.target.value })}
                />
              </div>
              <button className={ styled.main__auth__button }>Entrar</button>
              <Link href="/register" className={ styled.main__auth__link }>Criar conta</Link>
            </form>
          </div>

          <div className={ styled.main__social_medias }>
            <p className={ styled.main__social_medias__text }>Entrar com</p>
            <div className={ styled.main__social_medias__icons }>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <FacebookIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <GoogleIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
              <div className={ styled.main__social_medias__icons__icon_container }>
                <TwitterIcon className={ styled.main__social_medias__icons__icon_container__icon }/>
              </div>
            </div>
          </div>  
        </div>
      </div>
      <AlertNotification
        {...alertProps}
        state={ alertOpen }
        handleClose={() => setAlertOpen(false)}      
      />
    </div>
  );
}
