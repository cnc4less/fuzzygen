#ifndef _FUZZY_H
#	define _FUZZY_H
/* fuzzy.h
 * By: Travers Naran
 *
 * Small-memory footprint fuzzy logic library
 */


#	include <math.h>

// used to quickly define the truth curves without a lot of programming
#	define LEFT_CURVE(c, med, d)	m = fmax(m, category==(c) ? left(crispValue, (med), (d)) : 0)
#	define RIGHT_CURVE(c, med, d)	m = fmax(m, category==(c) ? right(crispValue, (med), (d)) : 0)
#	define CENTRE_CURVE(c, med, d)	m = fmax(m, category==(c) ? centre(crispValue, (med), (d)) : 0)


/**
 * Base class for defining new fuzzy domains and truth functions.  Create
 * a child class from this and implement minRange(), maxRange() and
 * membership().
 */
class FuzzyVariable {
	public:
		static const int MAX_CATEGORIES = 5;

		enum Hedge {
			NONE,
			A_LITTLE,
			SLIGHTLY,
			VERY,
			EXTREMELY,
			VERY_VERY,
			SOMEWHAT,
			INDEED
		};

	protected:
		static float centre(int x, int median, int deviation);
		static float left(int x, int median, int deviation);
		static float right(int x, int median, int deviation);

	public:
		virtual int minRange() const = 0;
		virtual int maxRange() const = 0;
		virtual float membership(int crispValue, int category) const = 0;
		static float hedge(Hedge hedge, float membership);
};


template<class T> class FuzzyInput
{
	private:
		T domain;
		int crispValue;

	public:
		void setCrispValue(int x) { crispValue = x; }

		float is(int category) const {
		   	return domain.membership(crispValue, category);
		}

		float is(FuzzyVariable::Hedge hedge, int category) const
		{
			return T::hedge(hedge, domain.membership(crispValue, category));
		}
};


template<class T,int MAX_CATEGORIES=5> class FuzzyOutput
{
	private:
		T domain;
		float m[MAX_CATEGORIES];

	public:
		/**
		 * Defuzzifies this variable and returns a crisp value.  Uses the
		 * centre-of-area algorithm.
		 */
		int getCrispValue()
		{
			// Perform numerical integration -- YAAAAY!
			int a = domain.minRange(), b = domain.maxRange();

			const int STEPS = 1024;

			// Calculate integration wedge size.  If less than 1, then default to 1
			// cause this is integer math anyway
			int d = (b - a) / STEPS;
			if (d < 1) d = 1;

			float totalWeight = 0.0f;
			float sum = 0.0f;
			for( int i = a; i <= b; i += d )
			{
				float thisValuesMembership = 0.0f;
				for( int category = 0; category < MAX_CATEGORIES; category++ )
				{
					float p = fmin(m[category], domain.membership(i, category));
					// printf("%d\t%d\t%f\t%f\n", i, category, m[category], membership(i, category));
					thisValuesMembership = fmax(thisValuesMembership, p);
				}
				totalWeight += thisValuesMembership;
				sum += i * thisValuesMembership;
			}

			return sum < 0.01f ? 0 : (int)rintf((sum / totalWeight));
		}


		void addMembership(int category, float membership)
		{
			m[category] = fmax(m[category], membership);
		}


		/**
		 * After each run of the engine, you must reset the output
		 * variables or bad results happen.
		 */
		void reset() { for(int i = 0; i < MAX_CATEGORIES; i++) m[i] = 0; }

};

class FuzzyLogic
{
	public:
		static float f_and(float a, float b) { return fmin(a, b); }
		static float f_or(float a, float b) { return fmax(a, b); }
		static float f_not(float a) { return 1 - a; }
};



#endif

