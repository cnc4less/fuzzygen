#include <stdio.h>
#include "fuzzy.h"


class Distance : public FuzzyVariable {
	public:
		static const int CLOSE = 0;
		static const int FAR = 1;

		int minRange() const { return 0; }
		int maxRange() const { return 300; }
		float membership(int crispValue, int category) const;
};

float Distance::membership(int crispValue, int category) const
{
	float m = 0.0f;
	LEFT_CURVE(CLOSE, 100, 50);
	RIGHT_CURVE(FAR, 100, 50);
	return m;
}


class Speed : public FuzzyVariable {
	public:
		static const int STOPPED = 0;
		static const int SLOW = 1;
		static const int MEDIUM = 2 ;
		static const int FAST = 3;

		int minRange() const { return 0; }
		int maxRange() const { return 255; }

		float membership(int crispValue, int category) const
		{
			float m = 0;
			CENTRE_CURVE(STOPPED, 0, 0);
			LEFT_CURVE(SLOW, 64, 64);
			CENTRE_CURVE(MEDIUM, 128, 64);
			RIGHT_CURVE(FAST, 196, 64);
			return m;
		}
};


class Direction : public FuzzyVariable
{
	public:
		static const int LEFT	=	0;
		static const int RIGHT	=	1;
		static const int AHEAD	=	2;

		int minRange() const { return -90; }
		int maxRange() const { return 90; }
		float membership(int crispValue, int category) const;
};

float Direction::membership(int crispValue, int category) const
{
	float m = 0;
	LEFT_CURVE(LEFT, -10, 10);
	RIGHT_CURVE(RIGHT, 10, 10);
	CENTRE_CURVE(AHEAD, 0, 30);
	return m;
}

FuzzyInput<Distance> obstructionAhead;
FuzzyInput<Direction> betterDirection;
FuzzyOutput<Speed> left, right;

void test()
{
	float m;

	left.reset();
	right.reset();

	// if obstructionAhead is far then left = fast, right = fast
	m = obstructionAhead.is(Distance::FAR);
	left.addMembership(Speed::MEDIUM, m);
	right.addMembership(Speed::MEDIUM, m);

	m = obstructionAhead.is(Distance::CLOSE);
	left.addMembership(Speed::SLOW, m);
	right.addMembership(Speed::SLOW, m);

	// if obstructionAhead is close and betterDirection is left then left = slow, right = fast
	m = betterDirection.is(Direction::LEFT);
	left.addMembership(Speed::SLOW, m);
	right.addMembership(Speed::FAST, m);

	m = betterDirection.is(Direction::RIGHT);
	left.addMembership(Speed::FAST, m);
	right.addMembership(Speed::SLOW, m);

	printf("Left=%d, Right=%d\n",
			left.getCrispValue(),
			right.getCrispValue());
}

int main(int argc, char *argv[])
{
	obstructionAhead.setCrispValue(200);
	test();

	obstructionAhead.setCrispValue(100);
	test();

	obstructionAhead.setCrispValue(50);
	test();

	obstructionAhead.setCrispValue(100);
	betterDirection.setCrispValue(-90);
	test();

	obstructionAhead.setCrispValue(100);
	betterDirection.setCrispValue(45);
	test();

	return 0;
}


