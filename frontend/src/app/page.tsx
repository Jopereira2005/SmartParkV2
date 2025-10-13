import Image from "next/image";
import styles from "./page.module.scss";

import { ArrowIcon } from './assets/Common/Arrow';

export default function Home() {
  return (
    <div className={ styles.home }>
      <div className={ styles.main }>
        <div className={ styles.main__welcome }>
          <div className={ styles.main__welcome__image }>
            <Image 
              src="/Avatar.png" 
              alt="Avatar" 
              width={90} 
              height={90}
            />
          </div>

          <div className={ styles.main__welcome__texts }>
            <h1 className={ styles.main__welcome__texts__title }>Bem Vindo, Mr Paxe 👋</h1>
            <div className={ styles.main__welcome__texts__div }></div>
            <div className={ styles.main__welcome__texts__address_container }>
              <div className={ styles.main__welcome__texts__address_container__address }>
                <h2 className={ styles.main__welcome__texts__address_container__address__title }>R.Smart Park, 98</h2>
                <p className={ styles.main__welcome__texts__address_container__address__description }>Conj. Hab Eng da Computação - Facens, Sorocaba - SP</p>
              </div>
              <ArrowIcon className={ styles.main__welcome__texts__address_container__arrow } />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
